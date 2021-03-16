$( document ).ready(
	function() {
		assign_input_events();
	}
);

function add_lemma() {
	if ($('#input_lemma').val() == '') {
		return;
	}
	$.ajax({
		url: curLang + "/add_lemma",
		data: $("#lex_form").serialize(),
		type: "GET",
		success: process_response,
		error: function(errorThrown) {
			alert( JSON.stringify(errorThrown) );
		}
	});
}

function add_lemma_anyway() {
	hide_modal();
	if ($('#input_lemma').val() == '') {
		return;
	}
	$.ajax({
		url: curLang + "/add_lemma_anyway",
		data: $("#lex_form").serialize(),
		type: "GET",
		success: process_response,
		error: function(errorThrown) {
			alert( JSON.stringify(errorThrown) );
		}
	});
}

function get_next_word() {
	var splitLines = $('#wf_list').val().split('\n');
	var nextLemma = splitLines.shift();
	$('#wf_list').val(splitLines.join('\n'));
	$('#input_lemma').val(nextLemma);
	$('#input_lexref').val('');
	$('#input_trans_ru').val(nextLemma);
	$('#input_pos').val($("#input_pos option:first").val());
	$('select.form-control').each(function(index) {
		$(this).val($(this).find("option:first").val());
	});
	$('input.form-check-input').each(function(index) {
		$(this).prop("checked", false);
	});
}

function process_response(data) {
	if (data.message) {
		$('#response_message').html(data.message);
		$('#response_message').toggleClass('show');
		setTimeout(function() { $('#response_message').toggleClass('show'); }, 1000);
		get_next_word();
	}
	else if (data.lexemes) {
		$('#lexeme_exists').modal('show');
		$('#old_lexemes').html(data.lexemes.join())
	}
}

function hide_modal() {
	$('#lexeme_exists').modal('hide');
}

function process_keypress(e) {
	if (e.key == "ArrowRight") {
		get_next_word();
	}
	else if (e.key == "Enter") {
		add_lemma();
	}
}

function assign_input_events() {
	$("#add_lemma").unbind('click');
	$("#add_lemma").click(add_lemma);
	$("#lexeme_exists_ok").unbind('click');
	$("#lexeme_exists_ok").click(add_lemma_anyway);
	$("#lexeme_exists_cancel").unbind('click');
	$("#lexeme_exists_cancel").click(hide_modal);
	
	$(document).keydown(process_keypress);
}