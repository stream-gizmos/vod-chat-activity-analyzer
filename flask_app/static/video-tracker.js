const STATE_STOP = "stop"
const STATE_PLAY = "play"

const shapeName = "video-tracker"
const shapeTemplate = {
    name: shapeName,
    type: "line",
    line: {
        dash: "dot",
        width: 1
    },
    fillcolor: "black",
    opacity: 0.5,
    y0: 0,
    y1: 1,
}

class VideoTracker {
    #graphId
    #enabled
    #seconds
    #state
    #currentTimeCallback

    #intervalId
    #refreshPeriod

    constructor(graphId) {
        this.#graphId = graphId
        this.#enabled = false
        this.#seconds = 0
        this.#currentTimeCallback = () => {}

        this.#refreshPeriod = 3000

        this.#clearInterval()
        this.onStop()
    }

    get graphId() {
        return this.#graphId
    }

    /**
     * @return {boolean}
     */
    get isEnabled() {
        return this.#enabled
    }

    /**
     * @param {Function} cb
     */
    setCurrentTimeCallback(cb) {
        this.#currentTimeCallback = cb
    }

    enable() {
        this.#enabled = true
    }

    disable() {
        this.#enabled = false
    }

    onPlay() {
        this.#state = STATE_PLAY

        setTimeout(async () => await this.#refreshPosition(this.#seconds), 0)

        this.#clearInterval()
        this.#intervalId = setInterval(async () => await this.#refreshPosition(), this.#refreshPeriod)
    }

    onStop() {
        this.#state = STATE_STOP

        this.#clearInterval()
    }

    /**
     * @param {number} seconds
     */
    onSeek(seconds) {
        if (!this.#isIntervalRunning) {
            setTimeout(async () => await this.#refreshPosition(seconds), 0)
        }
    }

    #normalizeSeconds(value) {
        return Math.floor(value * 1000) / 1000
    }

    #clearInterval() {
        clearInterval(this.#intervalId)
        this.#intervalId = undefined
    }

    /**
     * @return {boolean}
     */
    get #isIntervalRunning() {
        return !!this.#intervalId
    }

    /**
     * @param {number} [seconds]
     */
    async #refreshPosition(seconds) {
        if (typeof seconds === "undefined") {
            seconds = this.#currentTimeCallback()
        }

        const newSeconds = this.#normalizeSeconds(seconds)

        if (newSeconds === this.#seconds) {
            return
        }

        this.#seconds = newSeconds

        await this.#renderLines()
    }

    #getPlotNode() {
        return document.getElementById(this.graphId)
    }

    async #renderLines() {
        if (!this.isEnabled) {
            return
        }

        const $plot = this.#getPlotNode()
        const seconds = Math.floor(this.#seconds)

        const newShapes = getAllAxes($plot).map(plot => ({
            ...shapeTemplate,
            x0: seconds,
            x1: seconds,
            xref: plot[0],
            yref: `${plot[1]} domain`,
        }))

        const shapes = ($plot.layout.shapes || []).filter(s => s.name !== shapeName)
        shapes.push(...newShapes)

        await Plotly.relayout(this.graphId, {shapes})
    }
}

/**
 * @param {Node} $plot
 * @return {string[]}
 */
function getAllAxes($plot) {
    const xAxes = Object.keys($plot.layout)
        .filter(k => k.startsWith("xaxis"))

    const result = []
    for (const xAxis of xAxes) {
        result.push([
            `x${xAxis.substring(5)}`,
            $plot.layout[xAxis].anchor,
        ])
    }

    return result
}

/**
 * @param {VideoTracker} tracker
 */
function linkVideoTrackerWithTwitch(tracker, player) {
    player.addEventListener(Twitch.Player.PLAYING, () => {
        tracker.onPlay()
    })
    player.addEventListener(Twitch.Player.PAUSE, () => {
        tracker.onStop()
    })
    player.addEventListener(Twitch.Player.SEEK, ({position}) => {
        tracker.onSeek(position)
    })

    tracker.setCurrentTimeCallback(() => player.getCurrentTime())
    tracker.enable()
}

/**
 * @param {VideoTracker} tracker
 */
function linkVideoTrackerWithYoutube(tracker, player) {
    player.addEventListener("onStateChange", ({target, data}) => {
        if (data === YT.PlayerState.PLAYING) {
            tracker.onSeek(player.getCurrentTime())
            tracker.onPlay()
        }
        if (data === YT.PlayerState.PAUSED) {
            tracker.onStop()
        }
    })

    tracker.setCurrentTimeCallback(() => player.getCurrentTime())
    tracker.enable()
}
