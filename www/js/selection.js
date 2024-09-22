function updateSelection(selection, elements) {
  for (let i = 0; i < elements.length; i++) {
    let el = elements[i]
    if (selection.has(i)) {
      el.classList.remove("bg-gray-800");
      el.classList.add("bg-green-500");
    } else {
      el.classList.add("bg-gray-800");
      el.classList.remove("bg-green-500");
    }
  }
}

function makeSelectable(querySelector) {
  let selection = new Set()
  let elements = document.querySelectorAll(querySelector)
  for (let i = 0; i < elements.length; i++) {
    let el = elements[i]
    let n = i
    el.addEventListener("click", function () {
      if (selection.has(n)) {
        selection.delete(n)
      } else {
        selection.add(n)
      }
      updateSelection(selection, elements)
    })
  }
  return {
    clear: () => {
      selection = new Set()
      updateSelection(selection, elements)
    },
    get: () => [...selection].map(n => elements[n].dataset.pk),
  }
}
