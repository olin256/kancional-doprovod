// current_data
var current_teplate = null;
var current_stanza = 0;
var templates = null;
var song_data = null;
var cislo = null;
var transpose = 0;


async function fetch_template(cislo) {
    const response = await fetch("musicxml/"+cislo+".xml");
    const template = await response.text();
    return $.parseXML(template);
}

async function fetch_song_data(cislo) {
    const response = await fetch("song_data/"+cislo+".json");
    const song_data = await response.json();
    return song_data;
}


async function render_stanza(i) {
    current_stanza = i;
    stanza = song_data["stanzas"][i];
    stanza_sheet = stanza["stanza_sheet"];
    current_template = templates[stanza_sheet];
    return osmd.load(get_final_xml(
            current_template,
            stanza["lyrics"],
            song_data["stanza_lengths"][stanza_sheet])
    ).then(function() {
        osmd.Sheet.Transpose = transpose;
        osmd.updateGraphic();
        osmd.render();
    });
}

function update_stanza_selection() {
    $("#sloka_fieldset").children("input,label").remove();
    for (const [index, stanza] of song_data["stanzas"].entries()) {
        label = index+1;
        if (stanza["section"]) {
            label += " (" + stanza["section"] + ")";
        }
        new_html = '<input type="radio" name="sloka" value="'+index+'" id="sloka'+index+'"><label for="sloka'+index+'">'+label+'</label>';
        $("#sloka_fieldset").append(new_html);
    }
    $('input[type=radio][name=sloka]').on("change", function() {
        render_stanza(this.value);
    }).first().prop("checked", true);
    // $('input[type=radio][name=sloka]')
}

function song_change() {
    cislo = this.value;

    Promise.all([fetch_template(cislo+"-1"), fetch_song_data(cislo)]).then(function(responses) {
        current_template = responses[0];
        song_data = responses[1];
    }).then(function (r) {
        templates = new Object();
        templates[1] = current_template;
        render_stanza(0);

        update_stanza_selection();

    }).then(function (r) {
        extra_sheets = Object.keys(song_data["stanza_lengths"]).slice(1);
        Promise.all(extra_sheets.map(x => fetch_template(cislo+"-"+x))).then(function (responses) {
            extra_sheets.map(function(sheet_no, i) {
                templates[sheet_no] = responses[i];
            });
        });
    });
}


function lyrics_to_array(lyrics) {
    lyr_buffer = [];

    lyrics = lyrics.replaceAll(/\[:(.*?):\]/gs, "$1 $1");

    lyr_parts = lyrics.trim().split(/\s+/).map(function(s) {return s.replace("_", " ").split(/--?/);});

    for (i=0; i<lyr_parts.length; i++) {
        lp = lyr_parts[i];
        if (lp.length == 1) {
            lyr_buffer.push(["single", lp[0]]);
        } else {
            lyr_buffer.push(["begin", lp[0]]);
            for (j=1; j<lp.length-1; j++) {
                lyr_buffer.push(["middle", lp[j]]);
            }
            lyr_buffer.push(["end", lp.at(-1)]);
        }
    }

    return lyr_buffer;
}




function get_final_xml(template, lyrics, lengths) {

    // deep copy
    template = $(template.cloneNode(true));

    lyr_buffer = lyrics_to_array(lyrics);
    len_buffer = lengths.slice();
    skip = 0;

    template.find("#P1 voice").filter(function() {
        t = $(this);
        return (t.text()=="1") && !(t.siblings("rest").length);
    }).each(function() {
        if (skip == 0) {
            curr_repl = lyr_buffer.shift();
            skip = len_buffer.shift();
            if (!curr_repl) {
                curr_repl = ["single", "x"];
            }
            $(this).parent().append("<lyric><syllabic>"+curr_repl[0]+"</syllabic><text>"+curr_repl[1]+"</text></lyric>");
        } else {
            skip--;
        }
    });

    return template.get(0);
}


function do_transpose() {
    if (transpose == 0) {
        // re-render due to bug in OSMD Transpose
        render_stanza(current_stanza);
    } else {
        osmd.Sheet.Transpose = transpose;
        osmd.updateGraphic();
        osmd.render();
    }
}


function lyrics_above() {
    osmd.EngravingRules.LyricsYMarginToBottomLine = -1000;
    osmd.EngravingRules.LyricsYOffsetToStaffHeight = -9.0
}

function lyrics_center() {
    osmd.EngravingRules.LyricsYMarginToBottomLine = 0.2;
    osmd.EngravingRules.LyricsYOffsetToStaffHeight = 0.0;
}


$(document).ready(function() {
    pisen_select = $('select[name=pisen]').first();

    $.getJSON("selection.json", function(data) {
        data = Object.entries(data);
        // sort needed!
        data.sort((a, b) => a[0].localeCompare(b[0]));
        for (const [cislo, nazev] of data) {
            pisen_select.append("<option value='"+cislo+"'>"+cislo+" "+nazev+"</option>");
        }
        pisen_select.on("change", song_change);
        pisen_select.trigger('change');
    });

    $('input[type=radio][name=sloka]').on("change", function() {
        render_stanza(this.value);
    });
    $('input[type=radio][name=text_pos]').on("change", function() {
        if (this.value == "center") {
            lyrics_center();
        } else {
            lyrics_above();
        }
        osmd.updateGraphic();
        osmd.render();
    });
    $('#transp_plus').on("click", function() {
        transpose++;
        $("#transp").text(transpose);
        do_transpose();
    });
    $('#transp_minus').on("click", function() {
        transpose--;
        $("#transp").text(transpose);
        do_transpose();
    });
});