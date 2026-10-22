-- Run only after the intended admin account has registered.
-- Prefer the Flask CLI: set ADMIN_EMAIL, then run:
-- flask --app app make-admin
-- Manual alternative (replace the email carefully):
UPDATE users SET role='admin' WHERE email='admin@example.com';
