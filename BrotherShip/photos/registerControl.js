var sellerplatform = document.getElementById("sellerplat");
var buyerplatform = document.getElementById("buyerplat");

var registerType = document.querySelectorAll("button");
console.log(registerType);
for(var i=0; i < registerType.length; i++) {
  registerType[i].addEventListener("click", prompt);
}

function prompt(e) {
  e.preventDefault();
  if(e.target.value === "seller") {
    buyerplatform.style.display = "none";
    sellerplatform.style.display = "block";
  } else {
    buyerplatform.style.display = "block";
    sellerplatform.style.display = "none";
  }
}
