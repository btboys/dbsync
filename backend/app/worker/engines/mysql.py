from app.worker.engines.base import DatabaseEngine, ConnectionInfo


class MySQLEngine(DatabaseEngine):
    def _conn_args(self, info: ConnectionInfo) -> list[str]:
        return [
            f"--host={info.host}",
            f"--port={info.port}",
            f"--user={info.username}",
            f"--password={info.password}",
            info.database,
        ]

    def dump_cmd(self, info: ConnectionInfo, output_path: str, compression: bool) -> list[str]:
        cmd = ["mysqldump", "--single-transaction", "--routines", "--triggers",
               "--set-gtid-purged=OFF"]
        cmd.extend(self._conn_args(info))
        if compression:
            return ["sh", "-c", f"{' '.join(cmd)} | gzip > {output_path}"]
        cmd.append(f"--result-file={output_path}")
        return cmd

    def restore_cmd(self, info: ConnectionInfo, input_path: str) -> list[str]:
        if input_path.endswith(".gz"):
            return ["sh", "-c",
                    f"gunzip -c {input_path} | mysql {' '.join(self._conn_args(info))}"]
        return ["sh", "-c", f"mysql {' '.join(self._conn_args(info))} < {input_path}"]

    def get_tables_cmd(self, info: ConnectionInfo) -> list[str]:
        return ["mysql"] + self._conn_args(info) + [
            "-e", "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                  "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'",
            "--batch", "--skip-column-names",
        ]

    def transfer_schema_cmd(self, info: ConnectionInfo, dump_path: str) -> list[str]:
        cmd = ["mysqldump", "--no-data", "--routines"] + self._conn_args(info)
        return ["sh", "-c", f"{' '.join(cmd)} > {dump_path}"]
