import {computed} from "vue"
import Vue3Toasity, {toast} from "vue3-toastify"

const toastifyTheme = computed(() => {
    if (siteTheme.getCurrentTheme() === "dark") {
        return toast.THEME.DARK
    }

    return toast.THEME.LIGHT
})

export function installCommonPlugins(app) {
    app.use(Vue3Toasity, {
        theme: toastifyTheme,
    })

    return app
}
