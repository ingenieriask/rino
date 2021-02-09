$(document).ready(function(){

    // $("#id_item" ).autocomplete({
    //   source: "/correspondence/autocomplete",
    // });

    $('#id_current_user').selectpicker();
    $('#id_person').selectpicker();
    
    $("#id_document_file").fileinput({
        theme: 'fas',
        allowedFileExtensions: ['pdf'],
        overwriteInitial: false,
        maxFileSize:2000,
        maxFilesNum: 1,
        language: 'es',
        slugCallback: function (filename) {
            return filename.replace('(', '_').replace(']', '_');
        }
      });
});
