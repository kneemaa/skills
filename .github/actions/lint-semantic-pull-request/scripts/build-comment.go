package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"
)

type CommentData struct {
	LintError        string
	Diagnostic       string
	ErrorMessage     string
	HelpText         string
	CommitTypesTable string

	ShowLintSection bool
}

func main() {
	actionPath := os.Getenv("ACTION_PATH")
	if actionPath == "" {
		actionPath = "."
	}

	typesTable, err := os.ReadFile(filepath.Join(actionPath, "docs", "commit-types.md"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read commit-types.md: %v\n", err)
		os.Exit(1)
	}

	lintError := os.Getenv("LINT_ERROR")
	showLint := lintError != ""

	data := CommentData{
		LintError:        lintError,
		Diagnostic:       os.Getenv("DIAGNOSTIC"),
		ErrorMessage:     os.Getenv("ERROR_MESSAGE"),
		HelpText:         os.Getenv("HELP_TEXT"),
		CommitTypesTable: strings.TrimRight(string(typesTable), "\n"),

		ShowLintSection: showLint,
	}

	tmpl, err := template.ParseFiles(filepath.Join(actionPath, "templates", "comment.tmpl"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to parse template: %v\n", err)
		os.Exit(1)
	}

	if err := tmpl.Execute(os.Stdout, data); err != nil {
		fmt.Fprintf(os.Stderr, "failed to execute template: %v\n", err)
		os.Exit(1)
	}

	if ghOutput := os.Getenv("GITHUB_OUTPUT"); ghOutput != "" {
		f, err := os.OpenFile(ghOutput, os.O_APPEND|os.O_WRONLY, 0644)
		if err != nil {
			fmt.Fprintf(os.Stderr, "failed to open GITHUB_OUTPUT: %v\n", err)
			os.Exit(1)
		}
		defer f.Close()
		if data.LintError != "" {
			fmt.Fprintln(f, "has_errors=true")
		}
		if data.ShowLintSection {
			fmt.Fprintln(f, "has_content=true")
		}
	}
}
