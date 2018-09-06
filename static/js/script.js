$(document).ready(function(){

    $('#login').click(function(){
        console.log("entered login function");
        var json = {}
        var formdata = $("form#loginform").serializeArray();
        $.each(formdata,function(){
            json[this.name] = this.value || '';
        })
        $.ajax({
            type:'POST',
            url:'/api/existing_user',
            contentType:'application/json',
            data: JSON.stringify(json),
            dataType:'json',
            success: function(data){
                console.log("success");
                console.log(data);

                window.location='/';
            }
        });
    });

    $('#register').click(function(){
        console.log("entered register function");
        var json = {}
//        var form = document.getElementById("registerform");
        var formdata = $("form#registerform").serializeArray();
        $.each(formdata,function(){
            json[this.name] = this.value || '';
        })
        console.log(json);

        if (json["password"]!= json["confirm_password"]){
            console.log(json["password"]);
            document.getElementById('confirm_message').innerHTML= 'Passwords do NOT match!';
        }

        else{
            document.getElementById('confirm_message').innerHTML= '';
            $.ajax({
                type:'POST',
                url:'/api/users',
                contentType:'application/json',
                data: JSON.stringify(json),
                dataType:'json',
                success: function(data){
                    console.log("success");
                    console.log(data);
                }
            });

            document.getElementById('registerform').reset();

        }

    });

});






//$.fn.serializeObject = function()
//{
//    var o = {};
//    var a = this.serializeArray();
//    $.each(a, function() {
//        if (o[this.name] !== undefined) {
//            if (!o[this.name].push) {
//                o[this.name] = [o[this.name]];
//            }
//            o[this.name].push(this.value || '');
//        } else {
//            o[this.name] = this.value || '';
//        }
//    });

//    $.ajax({
//            type:'GET',
//            contentType: 'application/json',
//            data: JSON.stringify(formdata),
//            dataType:'json',
//            url: 'http:127.0.0.1:5000/api/token',
//            success: function(e){
//                console.log(e);
//            }
//            error:function(error){
//            console.log(error);
//            }
//        });
//
//
//    return o;
//};
//
//$(function() {
//    $('form').submit(function() {
//        $('#result').text(JSON.stringify($('form').serializeObject()));
//        return false;
//    });
//});