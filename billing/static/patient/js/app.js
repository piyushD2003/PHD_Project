AOS.init();
$(document).ready(function(){
	$('#scrollDown').click(function(){
	$('html, body').animate({scrollTop: 0/*$("#scrollDown").scrollTop()*/ }, 1000);
	});
});
function toggleSideBar(){
	var x = document.getElementById("sidebar").style.marginLeft;
	if(x=="200px"){
		document.getElementById("sidebar").style.marginLeft='0px';
		document.getElementById("main-content").style.margin='0 auto';
	}
	else{
		document.getElementById("sidebar").style.marginLeft='200px';
		document.getElementById("main-content").style.marginLeft='200px';
	}
}

// function toggleSideBar() {
// 	var sidebar = document.getElementById("sidebar");
// 	if (sidebar.style.left === "0px") {
// 	  // If it's open, hide it
// 	  sidebar.style.left = "-250px";
// 	} else {
// 	  // If it's hidden, show it
// 	  sidebar.style.left = "0px";
// 	}
//   }