// Маска для телефона: +7 (900) 123-45-67

function formatPhone(text) {
  // оставляем только цифры
  let digits = text.replace(/\D/g, "");

  // первую 7 или 8 убираем, потому что +7 мы добавим сами
  if (digits[0] == "7" || digits[0] == "8") {
    digits = digits.substring(1);
  }

  // в номере 10 цифр после +7
  digits = digits.substring(0, 10);

  let result = "+7";
  if (digits.length > 0) {
    result = result + " (" + digits.substring(0, 3);
  }
  if (digits.length > 3) {
    result = result + ") " + digits.substring(3, 6);
  }
  if (digits.length > 6) {
    result = result + "-" + digits.substring(6, 8);
  }
  if (digits.length > 8) {
    result = result + "-" + digits.substring(8, 10);
  }
  return result;
}

let phoneInput = document.getElementById("phone");

// поле телефона есть только на странице оформления заказа
if (phoneInput) {
  phoneInput.addEventListener("input", function () {
    phoneInput.value = formatPhone(phoneInput.value);
  });
}
