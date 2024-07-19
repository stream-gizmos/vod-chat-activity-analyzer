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

function onPointClick($plot, handler) {
    $plot.on("plotly_click", function (data) {
        if (!data.event.shiftKey) {
            return
        }

        const lines = data.points.filter(trace => trace.data.mode === "lines")
        const mainLine = lines.find(trace => trace.data.name === "15s") || lines[0]
        handler(mainLine.x, mainLine.y)
    })
}

/**
 * @param {number} td
 * @return {string}
 */
function timeDeltaToTime(td) {
    const sign = td < 0 ? "-" : ""
    let hours = Math.floor(Math.abs(td) / 3600)
    const remainder = Math.abs(td) - hours * 3600

    let minutes = Math.floor(remainder / 60)
    let seconds = remainder - minutes * 60

    if (hours < 10) {
        hours = `0${hours}`
    }
    if (minutes < 10) {
        minutes = `0${minutes}`
    }
    if (seconds < 10) {
        seconds = `0${seconds}`
    }

    return `${sign}${hours}:${minutes}:${seconds}`
}
