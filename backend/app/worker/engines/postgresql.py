from app.worker.engines.base import DatabaseEngine, ConnectionInfo


class PostgreSQLEngine(DatabaseEngine):
    def _env(self, info: ConnectionInfo) -> dict:
        return {"PGPASSWORD": info.password}

    def dump_cmd(self, info: ConnectionInfo, output_path: str, compression: bool) -> list[str]:
        cmd = ["pg_dump", "-Fc", "--no-owner",
               f"--host={info.host}", f"--port={info.port}",
               f"--username={info.username}", info.database]
        if compression:
            return ["sh", "-c",
                    f"PGPASSWORD='{info.password}' {' '.join(cmd)} | gzip > {output_path}"]
        return cmd + [f"--file={output_path}"]

    def restore_cmd(self, info: ConnectionInfo, input_path: str) -> list[str]:
        if input_path.endswith(".gz"):
            return ["sh", "-c",
                    f"gunzip -c {input_path} | PGPASSWORD='{info.password}' "
                    f"pg_restore --host={info.host} --port={info.port} "
                    f"--username={info.username} --dbname={info.database} --no-owner"]
        return ["pg_restore", f"--host={info.host}", f"--port={info.port}",
                f"--username={info.username}", f"--dbname={info.database}",
                "--no-owner", input_path]

    def get_tables_cmd(self, info: ConnectionInfo) -> list[str]:
        q = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
        return [
            "sh", "-c",
            f"PGPASSWORD='{info.password}' psql --host={info.host} --port={info.port} "
            f"--username={info.username} --dbname={info.database} "
            f"-Atc \"{q}\""
        ]

    def transfer_schema_cmd(self, info: ConnectionInfo, dump_path: str) -> list[str]:
        return ["sh", "-c",
                f"PGPASSWORD='{info.password}' pg_dump --schema-only --no-owner "
                f"--host={info.host} --port={info.port} "
                f"--username={info.username} {info.database} > {dump_path}"]
