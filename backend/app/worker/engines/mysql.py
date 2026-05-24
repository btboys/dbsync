import os
import subprocess
import tempfile

from app.worker.engines.base import DatabaseEngine, ConnectionInfo


class MySQLEngine(DatabaseEngine):
    SSL_FLAGS = ["--skip-ssl-verify-server-cert"]

    def _conn_args(self, info: ConnectionInfo) -> list[str]:
        return (
            [f"--host={info.host}", f"--port={info.port}",
             f"--user={info.username}", f"--password={info.password}"]
            + self.SSL_FLAGS
            + [info.database]
        )

    def dump(self, info: ConnectionInfo, output_path: str, compression: bool) -> str:
        cmd = ["mysqldump", "--single-transaction", "--routines", "--triggers"]
        cmd.extend(self._conn_args(info))

        if compression:
            target = output_path + ".sql.gz"
            # Write to temp file first, then move on success
            fd, tmp = tempfile.mkstemp(suffix=".sql.gz", dir=os.path.dirname(output_path))
            os.close(fd)
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                with open(tmp, "wb") as f:
                    gzip_proc = subprocess.Popen(
                        ["gzip"], stdin=proc.stdout, stdout=f, stderr=subprocess.PIPE,
                    )
                    _, stderr_bin = proc.communicate()
                    _, gzip_err_bin = gzip_proc.communicate()
                stderr = stderr_bin.decode("utf-8", errors="replace")
                if proc.returncode != 0:
                    raise RuntimeError(stderr.strip() or f"mysqldump exited with code {proc.returncode}")
                if gzip_proc.returncode != 0:
                    gzip_err = gzip_err_bin.decode("utf-8", errors="replace")
                    raise RuntimeError(gzip_err.strip() or f"gzip exited with code {gzip_proc.returncode}")
                os.rename(tmp, target)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
            return target
        else:
            target = output_path + ".sql"
            fd, tmp = tempfile.mkstemp(suffix=".sql", dir=os.path.dirname(output_path))
            os.close(fd)
            cmd.append(f"--result-file={tmp}")
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=3600)
                if result.returncode != 0:
                    if os.path.exists(tmp):
                        os.unlink(tmp)
                    stderr = result.stderr.decode("utf-8", errors="replace")
                    raise RuntimeError(stderr.strip() or f"mysqldump exited with code {result.returncode}")
                os.rename(tmp, target)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
            return target

    def restore_cmd(self, info: ConnectionInfo, input_path: str) -> list[str]:
        conn_args = self._conn_args(info)
        # Add --force to continue on errors (e.g. LOCK TABLES issues)
        conn_args_with_force = conn_args + ["--force"]
        if input_path.endswith(".gz"):
            return ["sh", "-c",
                    f"gunzip -c {input_path} | mysql {' '.join(conn_args_with_force)}"]
        return ["sh", "-c", f"mysql {' '.join(conn_args_with_force)} < {input_path}"]

    def get_tables_cmd(self, info: ConnectionInfo) -> list[str]:
        return ["mysql"] + self._conn_args(info) + [
            "-e", "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                  "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'",
            "--batch", "--skip-column-names",
        ]

    def transfer_schema_cmd(self, info: ConnectionInfo, dump_path: str) -> list[str]:
        cmd = ["mysqldump", "--no-data", "--routines"] + self._conn_args(info)
        return ["sh", "-c", f"{' '.join(cmd)} > {dump_path}"]
