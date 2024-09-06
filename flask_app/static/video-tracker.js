const STATE_STOP = "stop"
const STATE_PLAY = "play"

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
        this.#enabled = true
    }

    onPlay() {
        this.#state = STATE_PLAY

        clearTimeout(this.#intervalId)
        this.#intervalId = setInterval(() => {
            this.#refreshPosition()
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

    #refreshPosition() {
        this.#seconds = this.#normalizeSeconds(this.#currentTimeCallback())
        // console.log("refreshPosition seconds", this.#seconds)
    }
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
