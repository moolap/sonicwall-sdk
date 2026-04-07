package sonicwall

import "context"

// Commit applies all staged (pending) configuration changes.
func (c *Client) Commit(ctx context.Context) error {
	_, err := c.request(ctx, "POST", "/config/pending", nil)
	if err != nil {
		return &CommitError{Cause: err}
	}
	return nil
}

// Rollback discards all staged (pending) configuration changes.
func (c *Client) Rollback(ctx context.Context) error {
	_, err := c.request(ctx, "DELETE", "/config/pending", nil)
	if err != nil {
		return &RollbackError{Cause: err}
	}
	return nil
}

// Transaction executes fn inside a pending-config transaction.
// Commits on success, rolls back on any error returned by fn.
func (c *Client) Transaction(ctx context.Context, fn func(ctx context.Context) error) error {
	if err := fn(ctx); err != nil {
		// Best-effort rollback
		_ = c.Rollback(ctx)
		return err
	}
	return c.Commit(ctx)
}