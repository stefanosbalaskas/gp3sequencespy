args <- commandArgs(trailingOnly = TRUE)
repo_root <- if (length(args) >= 1L) normalizePath(args[[1L]], mustWork = TRUE) else normalizePath(".", mustWork = TRUE)
out_dir <- if (length(args) >= 2L) args[[2L]] else file.path(repo_root, "parity", "actual", "r")
tarball <- Sys.getenv("GP3SEQUENCES_R_TARBALL", unset = "")
expected_sha256 <- "1d2ca1d72ebd375292fc9bdd0f41848b8224f9e1ae9d34acbd9469f103bf5b8d"

if (!nzchar(tarball)) {
  stop("Set GP3SEQUENCES_R_TARBALL to the authoritative gp3sequences_0.3.0.tar.gz artifact.", call. = FALSE)
}
tarball <- normalizePath(tarball, mustWork = TRUE)
sha <- unname(tools::md5sum(tarball))
# Base R does not provide SHA-256. If sha256sum is present, enforce the frozen artifact hash.
sha256_bin <- Sys.which("sha256sum")
if (nzchar(sha256_bin)) {
  sha_line <- system2(sha256_bin, shQuote(tarball), stdout = TRUE, stderr = TRUE)
  actual_sha256 <- strsplit(sha_line[[1L]], "[[:space:]]+")[[1L]][[1L]]
  if (!identical(tolower(actual_sha256), expected_sha256)) {
    stop(sprintf("Frozen R tarball SHA-256 mismatch: expected %s, got %s.", expected_sha256, actual_sha256), call. = FALSE)
  }
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
lib <- tempfile("gp3sequences-oracle-lib-")
dir.create(lib, recursive = TRUE)
on.exit(unlink(lib, recursive = TRUE, force = TRUE), add = TRUE)

install.packages(tarball, repos = NULL, type = "source", lib = lib, dependencies = FALSE, quiet = TRUE)
suppressPackageStartupMessages(library(gp3sequences, lib.loc = lib, character.only = FALSE))
if (!identical(as.character(utils::packageVersion("gp3sequences", lib.loc = lib)), "0.3.0")) {
  stop("The installed oracle package is not gp3sequences 0.3.0.", call. = FALSE)
}

fixture <- utils::read.csv(file.path(repo_root, "parity", "fixtures", "minimal.csv"), stringsAsFactors = FALSE, check.names = FALSE)

write_table <- function(x, name) {
  utils::write.csv(x, file.path(out_dir, paste0(name, ".csv")), row.names = FALSE, na = "")
}

states <- summarise_sequence_states(fixture, "sequence_id", "sequence_order", "state")
write_table(states$overall, "state_summary_overall")

transitions <- summarise_sequence_transitions(fixture, "sequence_id", "sequence_order", "state")
write_table(transitions$overall, "transition_summary_overall")

paths <- format_sequence_paths(
  fixture,
  "sequence_id",
  "sequence_order",
  "state",
  metadata_cols = "group"
)
write_table(paths$paths, "formatted_paths")

extracted <- extract_sequence_ngrams(
  fixture,
  "sequence_id",
  "sequence_order",
  "state",
  min_length = 2L,
  max_length = 3L,
  overlap = "allow"
)
motifs <- summarise_sequence_motifs(extracted)
write_table(motifs$overall, "motif_summary_overall")

consensus <- create_consensus_sequence(fixture)
write_table(as.data.frame(consensus), "consensus")

distance <- as.matrix(compute_sequence_distance(fixture, method = "levenshtein"))
distance_out <- data.frame(sequence_id = rownames(distance), distance, check.names = FALSE, stringsAsFactors = FALSE)
write_table(distance_out, "distance_levenshtein")

writeLines(c(
  "package=gp3sequences",
  "version=0.3.0",
  paste0("tarball=", tarball),
  paste0("md5=", sha),
  paste0("expected_sha256=", expected_sha256),
  paste0("R.version=", R.version.string)
), file.path(out_dir, "oracle_metadata.txt"))

message("Wrote frozen R oracle outputs to: ", normalizePath(out_dir, mustWork = TRUE))
