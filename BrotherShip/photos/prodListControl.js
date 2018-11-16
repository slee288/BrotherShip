

var itemList = document.getElementById('items');
itemList.addEventListener('click', removeItem);

function removeItem(e){
  var Id = e.target.parentElement.children[2].innerHTML;
  var productID = Id.replace('productID:  ', '');
  if(e.target.classList.contains('delete')){
    if(confirm('Are you sure you want to delete product '+productID+'?')){
      var hidden = document.createElement('input');
      hidden.setAttribute("type","hidden");
      hidden.setAttribute('name', 'styleToDelete');
      hidden.setAttribute('value', productID);
      var place = e.target.parentElement.appendChild(hidden);
    } else {
      e.preventDefault();
    }
  } else if(e.target.classList.contains('edit')) {
    if(!confirm('Edit product '+productID+'?')){
      e.preventDefault();
    }
  }
}

var filterbyName = document.getElementById('filter');
filterbyName.addEventListener('change', filterItem);

var filterByCat = document.getElementById("filter2");
filterByCat.addEventListener('change', filterItem);

var itemList = document.getElementsByClassName('products');

function filterItem(e){
  var searchName = e.target.value;
  Array.from(itemList).forEach(function(item){
    if(e.target.id == "filter"){
      var itemName = item.children[1].id;
    } else {
      var itemName = item.children[4].id;
    }
    if(searchName == 'All'){
      item.style.display = 'block';
    }
    else if(searchName === itemName){
      item.style.display = 'block';
    } else{
      item.style.display = 'none';
    }
  });
}

var companyName = document.querySelectorAll("a.list-group-item-action");
for(var i = 0; i < companyName.length; i++) {
  companyName[i].addEventListener("click", action);
}

function action(e){
  for(var i = 0; i < itemList.length; i++) {
    itemList[i].style.display = "block";
  }
  filterbyName.value = "All";
  filterByCat.value = "All";
  if(e.target.id === 'company') {
    filterByCat.style.display = "none";
    filterbyName.style.display = "block";
  } else {
    filterByCat.style.display = "block";
    filterbyName.style.display = "none";
  }
}
