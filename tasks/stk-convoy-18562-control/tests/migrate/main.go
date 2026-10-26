// Build-time helper: apply the project's embedded migrations to the template database.
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/frain-dev/convoy/database/postgres"
	"github.com/frain-dev/convoy/internal/pkg/migrator"
)

func main() {
	dsn := os.Getenv("PGDSN")
	if dsn == "" {
		dsn = "postgres://convoy:convoy@127.0.0.1:5432/convoy_tmpl?sslmode=disable"
	}
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		fmt.Fprintf(os.Stderr, "connect: %v\n", err)
		os.Exit(1)
	}
	defer pool.Close()
	if err := migrator.New(postgres.NewFromConnection(pool)).Up(); err != nil {
		fmt.Fprintf(os.Stderr, "migrate: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("migrated")
}
