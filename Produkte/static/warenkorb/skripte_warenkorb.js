var URLS = {
  addItem:        '{% url "Warenkorb:cart-add" %}',
  removeItem:     '{% url "cart-remove" %}',
  changeQuantity: '{% url "cart-change-quantity" %}',
  emptyCart:      '{% url "cart-empty" %}',
}

var cart = {
    add: function (pk, quantity) {
      quantity = quantity || 1
      return $.post(URLS.addItem, {pk: pk, quantity: quantity}, 'json')
    },

    remove: function (itemPK) {
      return $.post(URLS.removeItem, {pk: itemPK}, 'json')
    },

    changeQuantity: function (pk, quantity) {
      return $.post(URLS.changeQuantity, {pk: pk, quantity: quantity}, 'json')
    },

    empty: function () {
      $.post(URLS.emptyCart, 'json')
    },
    
    title: 'Warenkorb'
};
