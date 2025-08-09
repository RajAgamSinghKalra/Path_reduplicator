import array
import oracledb
from .config import Config

def get_conn():
    # Thin mode defaults; use thick if you want.
    return oracledb.connect(user=Config.ORACLE_USER, password=Config.ORACLE_PASSWORD, dsn=Config.ORACLE_DSN)

def to_vec_array(vec_f32):
    """Convert an iterable of float32 values to :class:`array.array`.

    Oracle 23ai's driver can error (``DPY-3002``) when numpy arrays are
    bound directly.  Converting to ``array('f', ...)`` avoids this but we
    also validate the length so that mismatched embeddings are caught
    early.

    Parameters
    ----------
    vec_f32: iterable
        Sequence of float32 values representing an embedding.

    Returns
    -------
    array.array
        Array of type ``'f'`` with length equal to ``Config.VECTOR_DIM``.

    Raises
    ------
    ValueError
        If ``vec_f32`` does not have ``Config.VECTOR_DIM`` elements.
    """
    if len(vec_f32) != Config.VECTOR_DIM:
        raise ValueError(f"expected vector of length {Config.VECTOR_DIM}")
    return array.array('f', vec_f32)  # float32

def topk_by_vector(conn, query_vec, k):
    """
    Insert into query_identity, ANN-ish search with VECTOR_DISTANCE, then delete.
    Returns (customer_id, distance, lightweight fields).
    """
    qarr = to_vec_array(query_vec)
    cur = conn.cursor()
    # Insert the query vector
    cur.execute("INSERT INTO query_identity(qvec) VALUES (:1)", [qarr])
    cur.execute("SELECT qid FROM query_identity ORDER BY qid DESC FETCH FIRST 1 ROWS ONLY")
    qid = cur.fetchone()[0]

    sql = """
    WITH q AS (SELECT qvec FROM query_identity WHERE qid = :qid)
    SELECT c.customer_id,
           VECTOR_DISTANCE(c.identity_vec, q.qvec) AS vdist,
           c.full_name, c.dob, c.phone_e164, c.email_norm, c.gov_id_norm,
           c.addr_line, c.city, c.state, c.postal_code
    FROM customers c CROSS JOIN q
    ORDER BY vdist
    FETCH FIRST :k ROWS ONLY
    """
    cur.execute(sql, dict(qid=qid, k=k))
    rows = cur.fetchall()
    # Cleanup
    cur.execute("DELETE FROM query_identity WHERE qid = :qid", dict(qid=qid))
    conn.commit()
    return rows
