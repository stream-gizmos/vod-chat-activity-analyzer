function isVisible(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    return !$container.classList.contains("hidden")
}

function toggleVisibility(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    if (!isVisible(nodeId)) {
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

        if (!mainLine) {
            throw "Cannot find the main line for getting the time"
        }

        handler(mainLine.x, mainLine.y)
    })
}

function buildTwitchPlayer(nodeId, vodId) {
    const options = {
        width: "60%",
        video: vodId,
        autoplay: false,
        muted: false,
    }

    return new Twitch.Player(nodeId, options)
}

function buildYoutubePlayer(nodeId, vodId) {
    return new Promise((resolve, reject) => {
        let tries = 10
        const youtubeLibChecker = function () {
            if (tries < 0) {
                clearInterval(intervalId)
                reject('Failed to init YT lib')
                return
            }

            tries--

            if (!!window.YT?.loaded) {
                clearInterval(intervalId)
                resolve(new YT.Player(nodeId, {
                    width: "60%",
                    videoId: vodId,
                    playerVars: {
                        autoplay: 0,
                    },
                }))
            }
        }
        const intervalId = setInterval(youtubeLibChecker, 100)
    })
}
