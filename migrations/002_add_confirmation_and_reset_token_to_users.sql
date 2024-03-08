-- add confirmation email to token
-- performing the check to ensure there will be no errors when the scripts are ran multipel times and it won't block the next script.
DO $$
BEGIN
    IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'confirmation_token') THEN
        EXECUTE 'ALTER TABLE users ADD COLUMN confirmation_token VARCHAR(100)';
    END IF;

    IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'reset_token') THEN
        EXECUTE 'ALTER TABLE users ADD reset_token VARCHAR(100)';
    END IF;

    IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'reset_token_expiry') THEN
        EXECUTE 'ALTER TABLE users ADD reset_token_expiry TIMESTAMP';
    END IF;
END $$;