// Setup country select field
document.addEventListener("DOMContentLoaded", async () => {
  const flagDisplayEl = document.getElementById("flag-display");

  try {
    const res = await fetch("https://restcountries.com/v3.1/all");
    const countries = await res.json();

    new TomSelect("#country-select", {
      maxItems: 1,
      maxOptions: null,
      valueField: "value",
      searchField: "name",
      options: countries
        .sort((a, b) => a.name.common.localeCompare(b.name.common))
        .map((country) => ({
          value: country.cca2,
          name: country.name.common,
          flag: country.flags.svg,
        })),
      render: {
        option: function (data, escape) {
          return `<div class="option-container">
            <img src="${escape(
              data.flag
            )}" alt="Flag" style="width:20px;height:14px;vertical-align:middle;">
            ${escape(data.name)}
          </div>`;
        },
        item: function (data, escape) {
          return `<div style="background-color: #f0f0f0; padding: 3px; border-radius: 2px;">
            <img src="${escape(
              data.flag
            )}" alt="Flag" style="width:20px;height:14px;vertical-align:middle;">
            ${escape(data.name)}
          </div>`;
        },
      },
      onChange: function (value) {
        const selected = this.options[value];
        if (selected && selected.flag) {
          flagDisplayEl.innerHTML = `
            <img src="${selected.flag}" alt="Flag" style="width:100px;">
            <p>${selected.name}</p>
          `;
        } else {
          flagDisplayEl.innerHTML = "";
        }
      },
    });
  } catch (e) {
    console.error("載入國家資料失敗：", e);
    flagDisplayEl.textContent = "載入失敗，請稍後再試。";
  }
});

// Rules

let mockRules = [
  { country_code: "US", delay_percentage: 30, drop: false },
  { country_code: "CN", delay_percentage: 100, drop: true },
];

function displayRules(rules) {
  const tbody = document.querySelector("#rules-table tbody");
  tbody.innerHTML = "";
  rules.forEach((rule) => {
    const countryInfo = countryMap[rule.country_code] || {
      name: rule.country_code,
      flag: "",
    };
    const displayText = rule.drop ? "丟棄" : `稅率 ${rule.delay_percentage}%`;
    const tr = document.createElement("tr");
    tr.innerHTML = `
<td><img src="${countryInfo.flag}" style="width:20px;height:14px;vertical-align:middle;"> ${countryInfo.name}</td>
<td colspan="2">${displayText}</td>
<td>
  <button onclick="editRule('${rule.country_code}')">修改</button>
  <button onclick="deleteRule('${rule.country_code}')" class="destructive">刪除</button>
</td>`;
    tbody.appendChild(tr);
  });
}

function fetchRules() {
  fetch("/api/rules", {
    method: "GET",
  })
    .then((res) => res.json())
    .then((data) => displayRules(data.rules))
    .catch(() => {
      console.warn("使用 mockRules 模擬規則列表");
      displayRules(mockRules);
      console.warn("載入規則失敗");
    });
}

function addRule() {
  const country = document.getElementById("country-select").value;
  const drop = document.getElementById("drop-checkbox").checked;
  const delayInput = document.getElementById("delay-input");
  const delay = drop ? 0 : parseInt(delayInput.value);

  if (!country) return alert("請選擇國家");

  const body = JSON.stringify({
    country_code: country,
    delay_percentage: delay,
    drop,
  });

  const country_name = getCountryName(country);

  fetch(`/api/rules/${country}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => {
      fetchRules();
      if (drop) {
        changeNewsContext(
          `TRUMP BLOCKS ${country_name}'S PACKET FOREVER`,
          "Theyre out. Totally blocked. End of story."
        );
      } else {
        changeNewsContext(
          `TRUMP ANNOUNCES ${delay}% NEW TARIFF ON ${country_name}`,
          `They've been robbing us blind — not anymore. ${country_name}'s going to pay, big league.`
        );
      }
    })
    .catch(() => {
      changeNewsContext(
        "TRUMP BLAME POLITICIANS FOR ACTION FAILURE",
        "Unbelievable. We had it ready — but they stabbed people in the back."
      );
    });
}

function editRule(country_code) {
  // 先移除可能已存在的舊 modal
  const existingModal = document.getElementById("edit-rule-modal");
  if (existingModal) {
    existingModal.remove();
  }

  // 建立 modal 容器
  const modal = document.createElement("div");
  modal.id = "edit-rule-modal";
  modal.style.position = "fixed";
  modal.style.left = "50%";
  modal.style.top = "50%";
  modal.style.transform = "translate(-50%, -50%)";
  modal.style.backgroundColor = "white";
  modal.style.padding = "20px";
  modal.style.border = "1px solid #ccc";
  modal.style.borderRadius = "8px";
  modal.style.boxShadow = "0 4px 8px rgba(0,0,0,0.1)";
  modal.style.zIndex = "1000"; // 確保在最上層

  // Modal 內容
  modal.innerHTML = `
    <div style="text-align: right;">
      <button id="modal-cancel-button" class="close-button"></button>
    </div>
    <div id="form-group">
      <div style="font-size: larger;font-weight: bold;">修改規則 (${country_code})</div>
      <div class="form-inline">
        <label>丟棄封包</label>
        <input type="checkbox" id="modal-drop-checkbox" />
      </div>
      <div class="form-inline">
        <label>延遲百分比</label>
        <input
        type="number"
        id="modal-delay-input"
        min="0"
        max="100"
        value="0"
        />
      </div>
    </div>
    <div style="text-align: right;margin-top: 30px;">
      <button id="modal-confirm-button">確認</button>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.classList.add("modal-open");

  // 獲取 modal 內的元素
  const dropCheckbox = modal.querySelector("#modal-drop-checkbox");
  const delayInput = modal.querySelector("#modal-delay-input");
  const confirmButton = modal.querySelector("#modal-confirm-button");
  const cancelButton = modal.querySelector("#modal-cancel-button");

  // Drop checkbox 事件監聽
  dropCheckbox.addEventListener("change", function () {
    delayInput.disabled = this.checked;
    if (this.checked) {
      delayInput.value = ""; // 清空延遲值
    }
  });

  // 確認按鈕事件
  confirmButton.addEventListener("click", () => {
    const newDrop = dropCheckbox.checked;
    let newDelay = 0;

    if (!newDrop) {
      const delayValue = parseInt(delayInput.value, 10);
      if (isNaN(delayValue) || delayValue < 0) {
        alert("請輸入有效的延遲百分比");
        return;
      }
      newDelay = delayValue;
    }

    updateRule(country_code, newDelay, newDrop);
    modal.remove(); // 關閉 modal
    document.body.classList.remove("modal-open");
  });

  // 取消按鈕事件
  cancelButton.addEventListener("click", () => {
    modal.remove(); // 關閉 modal
    document.body.classList.remove("modal-open");
  });
}

function updateRule(country_code, delay_percentage, drop) {
  const body = JSON.stringify({
    delay_percentage: delay_percentage,
    drop,
  });

  const country_name = getCountryName(country_code);

  fetch(`/api/rules/${country_code}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body,
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => {
      fetchRules();
      if (drop) {
        changeNewsContext(
          `TRUMP BLOCKS ${country_name}'S PACKET FOREVER`,
          "We're getting rid of the garbage. We deserves strong, smart local network!"
        );
      } else {
        changeNewsContext(
          `TRUMP ANNOUNCES ${delay_percentage}% NEW TARIFF ON ${country_name}`,
          `The old rules were pathetic. We're bringing in something tremendous!`
        );
      }
    })
    .catch(() => {
      changeNewsContext(
        "TRUMP BLAME POLITICIANS FOR ACTION FAILURE",
        "Unbelievable. We had it ready — but they stabbed people in the back."
      );
    });
}

function deleteRule(country_code) {
  if (!confirm("確認刪除此規則？")) return;
  fetch(`/api/rules/${country_code}`, {
    method: "DELETE",
  })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then(() => {
      fetchRules();
      changeNewsContext(
        `NO MORE BLOCKS — FRIENDS NOW!`,
        "We're removing the rules and opening the doors. Local leads, Local wins."
      );
    })
    .catch(() => {
      changeNewsContext(
        "TRUMP BLAME POLITICIANS FOR ACTION FAILURE",
        "Unbelievable. We had it ready — but they stabbed people in the back."
      );
    });
}

function fetchPackets() {
  fetch("/api/packets", {
    method: "GET",
  })
    .then((res) => res.json())
    .then((data) => displayPackets(data.packets));
}

function displayPackets(packets) {
  const tbody = document.querySelector("#packet-table tbody");
  // tbody.innerHTML = ""; don't clear the table, just append new rows

  console.log("Packets:", packets);

  packets.forEach((p) => {
    const sourceInfo = countryMap[p.source_country] || {
      name: p.source_country,
      flag: "",
    };
    const statusText = p.status === "dropped" ? "丟棄" : "扣留中";

    const tr = document.createElement("tr");

    tr.innerHTML = `
<td>${p.url}</td>
<td>${p.source_ip}</td>
<td><img src="${
      sourceInfo.flag
    }" style="width:20px;height:14px;vertical-align:middle;"> ${
      sourceInfo.name
    }</td>
<td>${p.size}</td>
<td>${new Date(p.timestamp).toLocaleString()}</td>
<td>${p.rtt_time}ms</td>
<td>${p.retain_time}s</td>
<td><span class="badge ${p.status}">${statusText}</span></td>`;
    tbody.appendChild(tr);
  });
}

function clearPackets() {
  const tbody = document.querySelector("#packet-table tbody");
  tbody.innerHTML = "";
}

let countryMap = {};
function loadCountryMap() {
  fetch("https://restcountries.com/v3.1/all")
    .then((res) => res.json())
    .then((countries) => {
      countries.forEach((c) => {
        countryMap[c.cca2] = {
          name: c.name.common,
          flag: c.flags.svg,
        };
      });
      fetchRules();
      fetchPackets();
    });
}

document
  .getElementById("drop-checkbox")
  .addEventListener("change", function () {
    document.getElementById("delay-input").disabled = this.checked;
  });

setInterval(fetchPackets, 5000);
loadCountryMap();

function changeNewsContext(headline, revolving) {
  const newsHeadline = document.getElementById("news-headline");
  const newsRevolving = document.getElementById("news-revolving");

  newsHeadline.textContent = headline;
  newsRevolving.textContent = revolving;
}

function getCountryName(countryCode) {
  const country = countryMap[countryCode];
  return country ? country.name.toUpperCase() : countryCode;
}
