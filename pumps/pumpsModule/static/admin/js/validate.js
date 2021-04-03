var serviceHost='127.0.0.1';
var fleetsPort= '10002';

function devicesResponse(data){
   $("#id_vCustomerId").empty().append('<option value="" selected="selected">---------</option>');
   for(currentDriver in data.Drivers)
      $("#id_vCustomerId").append('<option value="' + data.Drivers[currentDriver].Id + '" >' + data.Drivers[currentDriver].Desc + '</option>')
}

$( document ).ready(function() {

   //Everytime the station changes loads the Cards  related to
   $( "#id_vStationId" ).change(function() {

      
         
        stationId= $( "#id_vStationId" ).val();

       $.ajax({
          url:'http://' + serviceHost + ':' + fleetsPort + '/fleetsModule/GetDevices/?stationId='+ stationId +'&format=jsonp&callback=devicesResponse',
           type:"POST",
           dataType: 'jsonp',
           jsonp: 'devicesResponse',
           async:'true',
           success:function (data) {
             }
           });
   });


   
      if($("#id_vCustomerId").val()!='---------')
      {
         var currentVal= $("#id_vCustomerId").val();
         var currentText= $( "#id_vCustomerId option:selected" ).text();

        $("#id_vCustomerId").empty().append('<option value="' + currentVal + '" selected="selected">' + currentText + '</option>');
      }
      
});





