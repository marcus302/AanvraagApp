CREATE DATABASE basic_testsuite;
CREATE DATABASE parsed_chunks_testsuite;

\c basic_testsuite;
CREATE EXTENSION IF NOT EXISTS vector;

\c parsed_chunks_testsuite;
CREATE EXTENSION IF NOT EXISTS vector;

\c mark;
CREATE EXTENSION IF NOT EXISTS vector;