import os
from typing import List, Dict
from dotenv import load_dotenv
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

load_dotenv()

host = os.getenv("DATABASE_HOST")
port = int(os.getenv("DATABASE_PORT", "5432"))
dbname = os.getenv("DATABASE_NAME", "postgres")
user = os.getenv("DATABASE_USER")
password = os.getenv("DATABASE_PASSWORD")

class SupabaseVectorDB:
    instance = None
    connection = None

    def __new__(cls, table: str = "documents"):
        if not cls.instance:
            cls.instance = super(SupabaseVectorDB, cls).__new__(cls)
            cls.instance._connect()
        return cls.instance
    

    def _connect(self):        
        try:
            if not self.connection:
                self.connection = psycopg.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password
                )
                self.connection.autocommit = True
        except Exception as e:
            self.__del__()
            print(f"Error connecting to the database: {e}")
            


    def __del__(self):
        if self.connection:
            self.connection.close()
            self.connection = None        
            
    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Return the closest rows for a vector embedding query.

        This version uses psycopg 3 only. The `query` argument must already be
        an embedding vector string or be replaced with your embedding-generation
        step before calling this method.
        """
        self._connect()
        assert self.connection is not None
        dims = 1536
        embedding_string = query
        query_sql = sql.SQL(
            """
            SELECT text_content, metadata
            FROM FQA_embedding
            ORDER BY embedding <-> {embedding}
            LIMIT {limit};
            """
        ).format(
            embedding=sql.Literal(embedding_string),
            limit=sql.Literal(top_k),
        )
        try:
            with self.connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query_sql)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []