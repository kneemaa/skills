package main

import (
	"bytes"
	"path/filepath"
	"strings"
	"testing"
	"text/template"
)

func render(t *testing.T, data CommentData) string {
	t.Helper()
	tmpl, err := template.ParseFiles(filepath.Join("..", "templates", "comment.tmpl"))
	if err != nil {
		t.Fatalf("parse template: %v", err)
	}
	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		t.Fatalf("execute template: %v", err)
	}
	return buf.String()
}

func TestRenderLintError(t *testing.T) {
	out := render(t, CommentData{
		ShowLintSection:  true,
		ErrorMessage:     "Hey there!",
		LintError:        `Unknown release type "fet"`,
		Diagnostic:       "Unknown type `fet`.",
		HelpText:         "**Examples:**",
		CommitTypesTable: "| Type | Bump |",
	})

	if !strings.Contains(out, "Hey there!") {
		t.Errorf("expected error message, got: %q", out)
	}
	if !strings.Contains(out, "> [!CAUTION]\n> Unknown release type") {
		t.Errorf("expected lint alert block, got: %q", out)
	}
	if !strings.Contains(out, "**Hint:** Unknown type") {
		t.Errorf("expected hint line, got: %q", out)
	}
	if !strings.Contains(out, "**Examples:**") {
		t.Errorf("expected help text, got: %q", out)
	}
	if !strings.Contains(out, "| Type | Bump |") {
		t.Errorf("expected commit types table, got: %q", out)
	}
}

func TestRenderLintErrorWithoutDiagnostic(t *testing.T) {
	out := render(t, CommentData{
		ShowLintSection:  true,
		ErrorMessage:     "Hey there!",
		LintError:        "Bad type",
		HelpText:         "**Examples:**",
		CommitTypesTable: "| Type | Bump |",
	})

	if strings.Contains(out, "**Hint:**") {
		t.Errorf("expected no hint line when Diagnostic is empty, got: %q", out)
	}
}

func TestRenderEmpty(t *testing.T) {
	out := render(t, CommentData{
		ErrorMessage:     "ignored",
		HelpText:         "ignored",
		CommitTypesTable: "ignored",
	})
	if strings.TrimSpace(out) != "" {
		t.Errorf("expected empty output when lint section is hidden, got: %q", out)
	}
}
