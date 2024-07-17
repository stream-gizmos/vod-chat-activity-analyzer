function toggleVisibility(playerContainerId) {
    const $container = document.querySelector(`#${playerContainerId}`)

    if (!$container) {
        return
    }

    if ($container.classList.contains("hidden")) {
        $container.classList.remove("hidden")
        $container.classList.add("visible")
    } else {
        $container.classList.remove("visible")
        $container.classList.add("hidden")
    }
}
