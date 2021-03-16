$( document ).ready(
	function() {
		assign_input_events();
	}
);

function add_lemma() {
	$.ajax({
		url: curLang + "/add_lemma",
		data: $("#lex_form").serialize(),
		type: "GET",
		success: check_if_exists,
		error: function(errorThrown) {
			alert( JSON.stringify(errorThrown) );
		}
	});
}

function check_if_exists(data) {
	$("#lex_form").html(data.contents);
}

function process_keypress(e) {
	if (e.key == "Enter") {
		add_lemma();
	}
}

function assign_input_events() {
	$("#add_lemma").unbind('click');
	$("#add_lemma").click(add_lemma);
	$(document).keydown(process_keypress);
}