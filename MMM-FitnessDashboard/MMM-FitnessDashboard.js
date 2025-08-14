Module.register("MMM-FitnessDashboard", {
    defaults: {
        updateInterval: 1000, // 1 giây cập nhật một lần
        stats: {
            pullups: 0,
            pushups: 0,
            squats: 0,
            heartRate: 0,
            breathRate: 0
        }
    },

    start() {
        this.updateTimer = setInterval(() => {
            // Giả lập dữ liệu, sau này sẽ lấy từ sensor thực
            this.config.stats.pullups += Math.floor(Math.random() * 2);
            this.config.stats.pushups += Math.floor(Math.random() * 3);
            this.config.stats.squats += Math.floor(Math.random() * 2);
            this.config.stats.heartRate = 70 + Math.floor(Math.random() * 20);
            this.config.stats.breathRate = 12 + Math.floor(Math.random() * 6);
            this.updateDom();
        }, this.config.updateInterval);
    },

    getStyles() {
        return [
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
            "MMM-FitnessDashboard.css"
  ];
    },

    getDom() {
        const wrapper = document.createElement("div");
        wrapper.className = "fitness-grid";

        const items = [
            { label: "Pull-Ups", value: this.config.stats.pullups, icon: '<i class="fas fa-arrow-up"></i>', color: "#ffffffff", max: 100 },
            { label: "Push-Ups", value: this.config.stats.pushups, icon: '<i class="fas fa-dumbbell"></i>', color: "#ffffffff", max: 100 },
            { label: "Squats", value: this.config.stats.squats, icon: '<i class="fas fa-person-running"></i>', color: "#ffffffff", max: 100 },
            { label: "Heart Rate", value: `${this.config.stats.heartRate} BPM`, icon: '<i class="fas fa-heartbeat"></i>', color: "#ffffffff", max: 200, pulse: true },
            { label: "Breath Rate", value: `${this.config.stats.breathRate} BrPM`, icon: '<i class="fas fa-wind"></i>', color: "#ffffffff", max: 50 }
        ];

        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "fitness-card";
            card.style.borderColor = item.color;

            const icon = document.createElement("div");
            icon.className = "fitness-icon";
            icon.innerHTML = item.icon;
            if (item.pulse) icon.classList.add("pulse");

            const label = document.createElement("div");
            label.className = "fitness-label";
            label.innerText = item.label;

            const value = document.createElement("div");
            value.className = "fitness-value";
            value.innerText = item.value;

            const progress = document.createElement("div");
            progress.className = "fitness-progress";
            const bar = document.createElement("div");
            bar.className = "fitness-bar";
            bar.style.backgroundColor = item.color;
            bar.style.width = Math.min((parseInt(item.value) / item.max) * 100, 100) + "%";
            progress.appendChild(bar);

            card.appendChild(icon);
            card.appendChild(label);
            card.appendChild(value);
            card.appendChild(progress);

            wrapper.appendChild(card);
        });

        return wrapper;
    }
});
