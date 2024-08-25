/**
 * @param {string} nodeId
 * @return {boolean}
 */
function isVisible(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return false
    }

    return !$container.classList.contains("hidden")
}

/**
 * @param {string} nodeId
 * @return {void}
 */
function toggleVisibility(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    $container.classList.toggle("hidden")
}

/**
 * @param {string} nodeId
 */
function show(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    $container.classList.remove("hidden")
}

/**
 * @param {string} nodeId
 */
function hide(nodeId) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    $container.classList.add("hidden")
}

/**
 * @param {string} text
 * @return {string}
 */
function normalizeId(text) {
    return text
        .replace(/\s+/g, '-')
        .replace(/[^a-zA-Z0-9]/g, '-')
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
        width: "100%",
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
                    width: "100%",
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

/**
 *
 * @param {string} nodeId
 * @param {string} videoHash
 * @param {object} emoticons
 * @param {string[]} selected
 * @return {void}
 */
function fillList(nodeId, videoHash, emoticons, selected) {
    const $container = document.querySelector(`#${nodeId}`)

    if (!$container) {
        return
    }

    for (let emote in emoticons) {
        const itemId = normalizeId(`${nodeId}-${emote}`)
        const item = `<li>
            <input id="${itemId}" type="checkbox" name="emoticons[${videoHash}][]" value="${emote}"/>
            <label for="${itemId}">${emote}
            <small>${emoticons[emote]}</small>
        </li>`
        $container.insertAdjacentHTML("beforeend", item)
        document.querySelector(`#${itemId}`).checked = selected.includes(emote)
    }
}
