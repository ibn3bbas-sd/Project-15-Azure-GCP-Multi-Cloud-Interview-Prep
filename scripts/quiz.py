#!/usr/bin/env python3
"""Flashcard quiz built from docs/*.md.

Every '### ' heading is a question; the text until the next heading is the answer.
Topic = file name without the number prefix (e.g. 'gcp-networking').
"""
import argparse
import random
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
REVIEW = Path(__file__).resolve().parent.parent / "review.md"


def load_cards():
    cards = []
    for md in sorted(DOCS.glob("*.md")):
        topic = re.sub(r"^\d+-", "", md.stem)
        question, answer = None, []
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.startswith("### "):
                if question:
                    cards.append((topic, question, "\n".join(answer).strip()))
                question, answer = line[4:].strip(), []
            elif line.startswith("## ") or line.startswith("# "):
                if question:
                    cards.append((topic, question, "\n".join(answer).strip()))
                question, answer = None, []
            elif question:
                answer.append(line)
        if question:
            cards.append((topic, question, "\n".join(answer).strip()))
    return cards


def main():
    p = argparse.ArgumentParser(description="Interview flashcards")
    p.add_argument("--topic", help="substring of topic, e.g. gcp, azure, terraform, hub-spoke")
    p.add_argument("-n", type=int, default=0, help="number of questions (0 = all)")
    p.add_argument("--list", action="store_true", help="list topics and counts")
    p.add_argument("--no-shuffle", action="store_true")
    args = p.parse_args()

    cards = load_cards()
    if args.list:
        counts = {}
        for t, _, _ in cards:
            counts[t] = counts.get(t, 0) + 1
        for t, c in counts.items():
            print(f"{c:4}  {t}")
        print(f"{len(cards):4}  TOTAL")
        return

    if args.topic:
        cards = [c for c in cards if args.topic.lower() in c[0].lower()]
    if not cards:
        sys.exit("No questions matched. Try --list.")
    if not args.no_shuffle:
        random.shuffle(cards)
    if args.n:
        cards = cards[: args.n]

    known, review = 0, []
    for i, (topic, q, a) in enumerate(cards, 1):
        print("\n" + "=" * 78)
        print(f"[{i}/{len(cards)}] ({topic})\n\n  {q}")
        try:
            input("\n  Think / answer out loud, then press Enter... ")
        except (EOFError, KeyboardInterrupt):
            break
        print("\n" + a + "\n")
        choice = input("  [k]new it / [r]eview later / [q]uit > ").strip().lower()
        if choice == "q":
            break
        if choice == "r":
            review.append((topic, q, a))
        else:
            known += 1

    print(f"\nScore: {known}/{known + len(review)} known.")
    if review:
        with REVIEW.open("w", encoding="utf-8") as f:
            f.write("# Review list\n\n")
            for t, q, a in review:
                f.write(f"### {q}  _({t})_\n{a}\n\n")
        print(f"Saved {len(review)} questions to {REVIEW.name}")


if __name__ == "__main__":
    main()
