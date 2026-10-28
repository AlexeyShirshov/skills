// Command levenshtein prints the Levenshtein distance between two words.
//
// Usage:
//
//	levenshtein <word1> <word2>
//	levenshtein              # reads the two words as two lines on stdin
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
)

func main() {
	a, b, err := words(os.Args[1:], os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, "levenshtein:", err)
		os.Exit(2)
	}
	fmt.Println(distance(a, b))
}

// words returns the two words to compare: the positional arguments when both
// are given, otherwise the first two lines read from r.
func words(args []string, r io.Reader) (string, string, error) {
	switch len(args) {
	case 2:
		return args[0], args[1], nil
	case 0:
	default:
		return "", "", fmt.Errorf("want two words, got %d arguments; usage: levenshtein <word1> <word2>", len(args))
	}

	sc := bufio.NewScanner(r)
	var lines []string
	for len(lines) < 2 && sc.Scan() {
		lines = append(lines, sc.Text())
	}
	if err := sc.Err(); err != nil {
		return "", "", err
	}
	if len(lines) < 2 {
		return "", "", fmt.Errorf("want two words: pass them as arguments or as two lines on stdin")
	}
	return lines[0], lines[1], nil
}

// distance returns the Levenshtein distance between a and b: the minimum
// number of insertions, deletions and substitutions, each costing 1.
// Transposition is not a separate operation.
//
// Both strings are compared rune by rune, so a multi-byte character counts as
// one letter, not as its UTF-8 bytes.
func distance(a, b string) int {
	ra, rb := []rune(a), []rune(b)

	// prev[j] is the distance between ra[:i] and rb[:j] for the previous i.
	prev := make([]int, len(rb)+1)
	for j := range prev {
		prev[j] = j
	}
	cur := make([]int, len(rb)+1)

	for i := 1; i <= len(ra); i++ {
		cur[0] = i
		for j := 1; j <= len(rb); j++ {
			cost := 1
			if ra[i-1] == rb[j-1] {
				cost = 0
			}
			cur[j] = min(prev[j]+1, cur[j-1]+1, prev[j-1]+cost)
		}
		prev, cur = cur, prev
	}
	return prev[len(rb)]
}
