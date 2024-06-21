\paper {
    text-font-size = #12
    ragged-bottom = ##t
    left-margin = 1.2\cm
    right-margin = 1\cm
    top-margin = 2\cm
    bottom-marin = 2\cm
    print-page-number = ##f
    scoreTitleMarkup = \markup { \italic \fromproperty #'header:piece }
    markup-system-spacing = #'((basic-distance . 2)
       (minimum-distance . 2)
       (padding . 1)
       (stretchability . 2))
    system-system-spacing = #'((basic-distance . 12)
       (minimum-distance . 6)
       (padding . 4)
       (stretchability . 2))
}

\layout {
    indent = #0
    \override Lyrics.LyricText.font-size = #0
    \context { \Score
        autoBeaming = ##f
        \omit BarNumber
        \override SpacingSpanner.spacing-increment = 2.4
    }
    \context { \Staff
        \consists Merge_rests_engraver
    }
}

\header {
    tagline = ""
}