# Generate a list of authors along with with commit count
git log | perl -e '%authors = (); while(<>){ $authors{$1}++ if /Author: (.+)/;  } foreach $author (sort { $authors{$b} <=> $authors{$a} } keys %authors){ printf("%s, %d commits\n", $author, $authors{$author}); }'

# Example output:
# 
# > John Smith <john@example.com>, 101 commits
# > Bob Doe <bob@example.com>, 32 commits
# > Billy Bob <billy@example.com>, 2 commits