\version "2.25.12"
\pointAndClickOff

% \header {
    % title = "TITLE"
    % subtitle = "SUBTITLE"
% }

\paper {
    % SYSTEM_COUNT
}

% VOICES

% LYRICS

% SCORE

\score {
    \header {
        % SCORE_TITLE
    }
    \transpose % TRANSPOSE {
    << \new PianoStaff
        <<
            \context Staff = "top" <<
                \context Voice = "soprano" { \voiceOne \soprano }
                \context Voice = "alto" { \voiceTwo \alto }
            >> 
            \new Lyrics \with { alignAboveContext = "top" } { \lyricsto "soprano" \SLOKA }
            \context Staff = "bottom" <<
                \context Voice = "tenor" { \voiceOne \tenor }
                \context Voice = "bass" { \voiceTwo \bass }
            >>
        >>
    >>
    }
}

