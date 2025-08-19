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
        fetch('http://localhost:5000/api/stats')
            .then(response => {
                // Kiểm tra nếu request không thành công
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Cập nhật dữ liệu từ API
                this.config.stats.pullups = data.pullups;
                this.config.stats.pushups = data.pushups;
                this.config.stats.squats = data.squats;
                this.config.stats.heartRate = data.heartRate;
                // Sửa lỗi chính tả từ "starts" thành "stats"
                this.config.stats.breathRate = data.breathRate;

                // Gọi hàm cập nhật giao diện
                this.updateDom();
            })
            .catch(error => {
                console.error('Lỗi khi lấy dữ liệu:', error);
            });
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
        
        // **Đây là phần đã được sửa lỗi**
        const numericalValue = typeof item.value === 'string'
            ? parseFloat(item.value)
            : item.value;

        const progress = document.createElement("div");
        progress.className = "fitness-progress";
        const bar = document.createElement("div");
        bar.className = "fitness-bar";
        bar.style.backgroundColor = item.color;
        // Sử dụng giá trị số đã được chuyển đổi để tính toán
        bar.style.width = Math.min((numericalValue / item.max) * 100, 100) + "%";
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
