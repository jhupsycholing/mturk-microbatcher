
        $('.disabled').click(function(e){
          e.preventDefault();
        });
        $(document).ready(function() {
          turkSetAssignmentID();
          //var consentFirst = '{{ consent }}';
          var consentFirst = $('#consentFirst').text();
          var require_headphones = $('#require_headphones').text();
          consentFirst = (consentFirst == 'True');
          //var require_headphones = '{{ headphone }}';
          require_headphones = (require_headphones == 'True');
          var headphoneCheckConfig = {jsonPath:'/getFile?filename=wavJson.json'};

          if(consentFirst && require_headphones)
            $('#consent').css('display','block');
          if(consentFirst && !(require_headphones))
            $('#consent').css('display','block');
          if(!(consentFirst) && !(require_headphones))
            $('#mainpage').css('display','block');
          if(!(consentFirst) && require_headphones){
            console.log('checking headphones');
            HeadphoneCheck.runHeadphoneCheck(headphoneCheckConfig);
            $('#consent').css('display','none');
          }
          //if(consentFirst)
          

          $('#toSurveyPage').click(function(){
            if(require_headphones){
              console.log('checking headphones');
              HeadphoneCheck.runHeadphoneCheck(headphoneCheckConfig);
              $('#consent').css('display','none');
            }
            else{
              $('#consent').css('display','none');
              $('#mainpage').css('display','block');
            }
          });
        /* 4) Define what to do when the headphone check finishes */
          $(document).on('hcHeadphoneCheckEnd', function(event, data) {
            var headphoneCheckDidPass = data.didPass;
            var headphoneCheckData = data.data;
            var didPassMessage = headphoneCheckDidPass ? 'passed' : 'failed';
            console.log(didPassMessage);

            if(headphoneCheckDidPass){
              $('#mainpage').css('display','block');
            }
            else
              $('#failpage').css('display','block');

          });

          //var headphoneCheckConfig = {};
          /* 5) Run the headphone check, with customization options defined in headphoneCheckConfig */
          
          
          //else

        });
        var oldURL = $('#link').attr('href');
        var assignmentId = turkGetParam('assignmentId','');
        var hitId = turkGetParam('hitId','');
        var workerId = turkGetParam('workerId','');
        var res = '';
        var newURL = '/ibex' + "?assignmentId="+assignmentId+"&HITId="+ hitId+"&workerId="+workerId;
        $('#assignmentId').val(assignmentId);
        $('#hitId').val(hitId);
            
        if (assignmentId != "ASSIGNMENT_ID_NOT_AVAILABLE") {
          $('#link').attr('href',newURL);
        }
        var changeTimer = false;
        //$('#')
        $('#code').on('input',function(){
                if(changeTimer !== false) {
                  clearTimeout(changeTimer);
                  changeTimer = false;
                }
                changeTimer = setTimeout(function(){
                  $('#submit').val('confirming...please wait');
                    $.ajax({
                      type:'GET',
                      data:{
                        code: $('#code').val(),
                        hitId:hitId,
                        assignmentId: assignmentId

                      },
                      dataType:'json',
                      contentType:'application/json',
                      url: '/submit',
                      success: function(response) {
                        console.log('success');
                        console.log(response);
                        res = response;
                        if(response['valid'] === 'true'){
                          console.log('valid');
                          $('#submitButton').val('Submit');
                          $('#submitButton').prop('disabled',false);
                          $('#survey').text('Survey Code: (CORRECT SURVEY CODE)');
                        }
                        else if(response['valid'] === 'nosub'){
                          $('#survey').text('Survey Code: (YOU MUST FIRST VISIT THE SURVEY LINK)')
                        }
                        else{
                          console.log('code');
                          $('#survey').text('Survey Code: (INCORRECT SURVEY CODE)');
                        }
                      },
                      error: function(response) {
                        console.log('error');
                        $('#submitButton').val('Submit');
                        $('#submitButton').prop('disabled',false);
                      }
                    });
                    changeTimer = false;
                },300);
                changeTimer = true;
            });
