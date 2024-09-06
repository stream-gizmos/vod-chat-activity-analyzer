const STATE_STOP = "stop"
const STATE_PLAY = "play"

const shapeName = "video-tracker"
const shapeTemplate = {
    "name": shapeName,
    "type": "line",
    "line": {
        "dash": "dot",
        "width": 1
    },
    "fillcolor": "black",
    "opacity": 0.5,
    "y0": 0,
    "y1": 1,
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

        this.#intervalId = undefined
        this.#refreshPeriod = 1000

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

        clearTimeout(this.#intervalId)
        this.#intervalId = setInterval(async () => {
            await this.#refreshPosition()
        }, this.#refreshPeriod)
    }

    onStop() {
        this.#state = STATE_STOP

        clearTimeout(this.#intervalId)
    }

    /**
     * @param {number} seconds
     */
    onSeek(seconds) {
        this.#seconds = this.#normalizeSeconds(seconds)
        // console.log("onSeek seconds", this.#seconds)
    }

    #normalizeSeconds(value) {
        return Math.floor(value * 1000) / 1000
    }

    async #refreshPosition() {
        this.#seconds = this.#normalizeSeconds(this.#currentTimeCallback())

        await this.#renderShapes()
    }

    #getPlotNode() {
        return document.getElementById(this.graphId)
    }

    async #renderShapes() {
        if (!this.isEnabled) {
            return
        }

        const $plot = this.#getPlotNode()

        const seconds = Math.floor(this.#seconds)
        const shapes = []
        for (const plot of getAllAxes($plot)) {
            shapes.push({
                ...shapeTemplate,
                x0: seconds,
                x1: seconds,
                xref: plot[0],
                yref: `${plot[1]} domain`,
            })
        }

        if (typeof $plot.layout.shapes === "undefined") {
            $plot.layout.shapes = []
        }

        $plot.layout.shapes = $plot.layout.shapes.filter(s => s.name !== shapeName)
        $plot.layout.shapes.push(...shapes)

        await Plotly.relayout(this.graphId, $plot.layout)
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
        console.log("Twitch.Player.PLAYING")
        tracker.onPlay()
        tracker.onSeek(player.getCurrentTime())
    })
    player.addEventListener(Twitch.Player.PAUSE, () => {
        console.log("Twitch.Player.PAUSE")
        tracker.onStop()
        tracker.onSeek(player.getCurrentTime())
    })
    player.addEventListener(Twitch.Player.SEEK, ({position}) => {
        console.log("Twitch.Player.SEEK")
        tracker.onSeek(position)
    })

    tracker.setCurrentTimeCallback(() => player.getCurrentTime())
    tracker.enable()
}
