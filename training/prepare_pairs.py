"""
Create a CSV with columns:
query_full_name,query_dob,query_phone,query_email,query_gov_id,query_addr,query_city,query_state,query_pc,query_ctry,
cand_customer_id,label

Populate this by sampling real queries and the customer_id of either the true match (label=1)
or a hard negative (label=0).
"""
