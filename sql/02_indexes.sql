-- Metadata indexes for cheap blocking
CREATE INDEX idx_customers_phone ON customers(phone_e164);
CREATE INDEX idx_customers_email ON customers(email_norm);
CREATE INDEX idx_customers_govid ON customers(gov_id_norm);

-- NOTE: Some Oracle 23ai editions have experimental/GA vector indexes.
-- If your edition supports it, consult your exact version docs and create one on identity_vec.
-- Otherwise, ORDER BY VECTOR_DISTANCE(identity_vec, :q) FETCH FIRST K works well for K ~ 100-1000 on mid-scale.
