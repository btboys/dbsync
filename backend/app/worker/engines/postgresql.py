import os
import subprocess
import tempfile

from app.worker.engines.base import DatabaseEngine, ConnectionInfo


class PostgreSQLEngine(DatabaseEngine):
    def _env(self, info: ConnectionInfo) -> dict:
        return {"PGPASSWORD": info.password}

    def dump(self, info: ConnectionInfo, output_path: str, compression: bool) -> str:
        cmd = ["pg_dump", "-Fc", "--no-owner",
               f"--host={info.host}", f"--port={info.port}",
               f"--username={info.username}", info.database]
        env = {"PGPASSWORD": info.password}
        if compression:
            target = output_path + ".dump.gz"
            fd, tmp = tempfile.mkstemp(suffix=".dump.gz", dir=os.path.dirname(output_path))
            os.close(fd)
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                )
                with open(tmp, "wb") as f:
                    gzip_proc = subprocess.Popen(
                        ["gzip"], stdin=proc.stdout, stdout=f, stderr=subprocess.PIPE,
                    )
                    _, stderr_bin = proc.communicate()
                    _, gzip_err_bin = gzip_proc.communicate()
                stderr = stderr_bin.decode("utf-8", errors="replace")
                if proc.returncode != 0:
                    raise RuntimeError(stderr.strip() or f"pg_dump exited with code {proc.returncode}")
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
            target = output_path + ".dump"
            cmd.append(f"--file={target}")
            result = subprocess.run(cmd, capture_output=True, timeout=3600, env=env)
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace")
                raise RuntimeError(stderr.strip() or f"pg_dump exited with code {result.returncode}")
            return target

    def restore_cmd(self, info: ConnectionInfo, input_path: str) -> list[str]:
        env = f"PGPASSWORD='{info.password}'"
        if input_path.endswith(".gz"):
            return ["sh", "-c",
                    f"gunzip -c {input_path} | {env} "
                    f"pg_restore --host={info.host} --port={info.port} "
                    f"--username={info.username} --dbname={info.database} --no-owner"]
        return ["pg_restore", f"--host={info.host}", f"--port={info.port}",
                f"--username={info.username}", f"--dbname={info.database}",
                "--no-owner", input_path]

    def get_tables_cmd(self, info: ConnectionInfo) -> list[str]:
        q = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
        env = f"PGPASSWORD='{info.password}'"
        return [
            "sh", "-c",
            f"{env} psql --host={info.host} --port={info.port} "
            f"--username={info.username} --dbname={info.database} "
            f"-Atc \"{q}\""
        ]

    def transfer_schema_cmd(self, info: ConnectionInfo, dump_path: str) -> list[str]:
        env = f"PGPASSWORD='{info.password}'"
        return ["sh", "-c",
                f"{env} pg_dump --schema-only --no-owner "
                f"--host={info.host} --port={info.port} "
                f"--username={info.username} {info.database} > {dump_path}"]
