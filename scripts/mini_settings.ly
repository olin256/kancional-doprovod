\pointAndClickOff
#(set-global-staff-size 2)
break = {}
\layout {
    \autoBreaksOff
    \override Beam.color = "#00FF00"
    \override Stem.color = "#FF0000"
    % \omit Staff.NoteHead
    \omit Staff.Flag
    \omit Staff.Slur
    \omit Staff.Dots
    \omit Staff.Rest
    \omit Staff.BreathingSign
    \context {
        \Staff
        \remove Staff_symbol_engraver
        \remove Accidental_engraver
        \remove Bar_engraver
        \remove Clef_engraver
        \remove Instrument_name_engraver
        \remove Key_engraver
        \remove Text_engraver
        \remove Time_signature_engraver
    }
    \context {
        \Lyrics
        \remove Lyric_engraver
        \remove Hyphen_engraver
        \remove Extender_engraver
        \remove Stanza_number_engraver
    }
}