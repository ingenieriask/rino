$(document).ready(function(){

    // $("#id_item" ).autocomplete({
    //   source: "/correspondence/autocomplete",
    // });

    //$('#id_current_user').selectpicker();
    //$('#id_person').selectpicker();
    
    $("#id_document_file").fileinput({
        theme: 'fas',
        allowedFileExtensions: ['pdf'],
        overwriteInitial: true,
        maxFileSize:2000,
        maxFilesNum: 1,
        language: 'es',
        slugCallback: function (filename) {
            return filename.replace('(', '_').replace(']', '_');
        }
      });

      $('#id_office').on('change',function(evt){
        console.log("cambio !!!");
        console.log(this.value);
        $('#id_doctype').html('<option>Example 1</option><option>Example2</option>').selectpicker('refresh');

      });

      console.log("Termina la ejecución");
});
