var course_id;

function teacher_select_change(elem) {

    var prompt = "#" + elem['id'];
    foo = prompt.split('_');
    var course_ndx = foo[2];
    var v =  $(prompt + " option:selected").val(); 
    foo = v.split('_');
    course_id = foo[0];
    teacher_id = foo[1];
    var teacher_period = parseInt($(prompt).parent().parent().find('td:eq(3)').text());
    //Appel JSON pour mettre à jour la base données
    $.getJSON('/course/' + course_id + '/' + teacher_id, function(data) {
        if (data.length > 0) {
            $.each(data, function(index) {
                if(this.result == 'OK') {
                    var json = this;
                    $("#control_tab tr").each(function() {
                        if( $(this).attr('id') == 'teacher_'+json.id) {
                            $(this).find('td:eq(1)').text(json.teaching);
                            $(this).find('td:eq(2)').text(json.mission);
                            $(this).find('td:eq(3)').text(json.supervision);
                            $(this).find('td:eq(4)').text(json.others);
                            $(this).find('td:eq(5)').text(json.total);
                            $(this).find('td:eq(6)').text(json.gap);
                        }
                    });
                }
                else {
                    alert('Une erreur s\'est produite au chargement des données AJAX');
                }
            });
        }
    });
    return false;
}
