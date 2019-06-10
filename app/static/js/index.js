$(document).ready(function() {
  /* 4) Define what to do when the headphone check finishes */
  $(document).on('hcHeadphoneCheckEnd', function(event, data) {
    var headphoneCheckDidPass = data.didPass;
    var headphoneCheckData = data.data;
    var didPassMessage = headphoneCheckDidPass ? 'passed' : 'failed';
    console.log(didPassMessage)
    alert('Screening task ' + '.');
  });

  var headphoneCheckConfig = {};
  /* 5) Run the headphone check, with customization options defined in headphoneCheckConfig */
  HeadphoneCheck.runHeadphoneCheck(headphoneCheckConfig);
});