-- Metadata indexes for cheap blocking
CREATE INDEX idx_customers_phone ON USERS.CUSTOMERS(phone_e164);
CREATE INDEX idx_customers_email ON USERS.CUSTOMERS(email_norm);
CREATE INDEX idx_customers_govid ON USERS.CUSTOMERS(gov_id_norm);

-- NOTE: Some Oracle 23ai editions have experimental/GA vector indexes.
-- If your edition supports it, consult your exact version docs and create one on identity_vec.
-- Otherwise, ORDER BY VECTOR_DISTANCE(identity_vec, :q) FETCH FIRST K works well for K ~ 100-1000 on mid-scale.
