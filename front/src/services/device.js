function generateDeviceId() {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);

    return Array.from(array)
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
}

export function getDeviceId() {
    let deviceId = localStorage.getItem("device_id_V7");

    if (!deviceId) {
        deviceId = generateDeviceId();
        localStorage.setItem("device_id_V7", deviceId);
    }

    return deviceId;
}

export function getDeviceName() {
    const userAgent = navigator.userAgent;

    let os = "web";

    if (userAgent.includes("Windows")) {
        os = "Windows";
    } else if (userAgent.includes("Mac OS")) {
        os = "macOS";
    } else if (userAgent.includes("Android")) {
        os = "Android";
    } else if (userAgent.includes("iPhone")) {
        os = "iOS";
    } else if (userAgent.includes("Linux")) {
        os = "Linux";
    }

    return `web_${os}`;
}