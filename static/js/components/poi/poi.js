import stateManager from "../../state/mapStateManager.js";
import { LanguageService } from "../../services/LanguageService.js";
import { getBoundsPadding } from "../../utils/utils.js";
import { ANIMATION_DURATION } from "../../constants.js";

export const poiInfo = [
    {
        title_ru: "Абхазская железная дорога",
        title_en: "Abkhazian railway",
        title_ka: "აფხაზეთის რკინიგზა",
        description_ru: "Абхазская железная дорога на сегодняшний день не соединена с Грузинской железной дорогой. После станции Очамчире рельсы разобраны, никакой инфраструктуры нет. Однако, пассажирское сообщение в Абхазии существует: поезда ходят до Сухуми со стороны России. Например, действуют поезда из Москвы и Санкт-Петербурга. Их расписание не сложно найти в интернете, на этом сайте о них не рассказывается.",
        description_en: "Abkhazian railway is not connected to the Georgian railway. After the Ochamchire station, the rails are dismantled, there is no infrastructure. However, passenger communication in Abkhazia exists: trains run to Sukhumi from Russia. For example, there are trains from Moscow and St. Petersburg. Their schedule is not difficult to find online, this site does not talk about them.",
        description_ka: "აფხაზეთის რკინიგზა დღესდღეობით არ უკავშირდება საქართველოს რკინიგზას. ოჩამჩირის სადგურის შემდეგ რელსები დაშლილია, ინფრასტრუქტურა არ არსებობს. თუმცა, აფხაზეთში სამგზავრო მიმოსვლა არსებობს: მატარებლები დადიან სოხუმამდე რუსეთის მხრიდან. მაგალითად, მოქმედებს მატარებლები მოსკოვიდან და სანკტ-პეტერბურგიდან. მათი განრიგის მოძიება ინტერნეტში არ არის რთული, ამ საიტზე მათ შესახებ არაფერია ნათქვამი.",
        coords: [42.7732, 41.3948],
    },
    {
        title_ru: "Ткибули",
        title_en: "Tkibuli",
        title_ka: "ტყიბული",
        description_ru: "Пассажирские поезда в Ткибули не ходят как минимум с 2023 года. До города можно добраться на маршрутке.",
        description_en: "Passenger trains in Tkibuli do not run as of 2023. To the city you can get by bus.",
        description_ka: "სამგზავრო მატარებლები ტყიბულში არ დადიან სულ მცირე 2023 წლიდან. ქალაქამდე შეგიძლიათ მიხვიდეთ მარშრუტკით.",
        coords: [42.33774, 42.98264],
    },
    {
        title_ru: "Кахетия",
        title_en: "Kakheti",
        title_ka: "კახეთი",
        description_ru: "Пассажирские поезда в Кахетию не ходят с 2007 года. Новостей о планах возобновления пассажирских перевозок пока нет.",
        description_en: "Passenger trains in Kakheti do not run since 2007. There are no news about plans to resume passenger transportation.",
        description_ka: "სამგზავრო მატარებლები კახეთში არ დადიან 2007 წლიდან. სამგზავრო გადაზიდვების განახლების გეგმების შესახებ ჯერჯერობით სიახლეები არ არის.",
        coords: [41.6467, 45.6118],
    },
    {
        title_ru: "Ветка Боржоми — Ахалцихе",
        title_en: "Borjomi — Akhaltsikhe line",
        title_ka: "ბორჯომი — ახალციხის ხაზი",
        description_ru: "Крайняя точка для пассажирских поездов на этой ветке - Боржоми. В сторону Ахалцихе поезда не ходят с 2010 года. В мае 2026 года руководство Грузинских железных дорог анонсировало возобновление движения до Ахалцихе, но без конкретных сроков.",
        description_en: "The farthest point for passenger trains on this branch is Borjomi. Passenger trains to Akhaltsikhe do not run since 2010. In May 2026, Georgian Railway management announced the resumption of service to Akhaltsikhe, but without a specific timeline.",
        description_ka: "მგზავრული მატარებლებისთვის ამ ხაზზე საბოლოო წერტილია ბორჯომი. ახალციხის მიმართულებით მატარებლები 2010 წლიდან აღარ მოძრაობენ. 2026 წლის მაისში საქართველოს რკინიგზის ხელმძღვანელობამ გამოაცხადა ახალციხემდე მიმოსვლის განახლება, თუმცა კონკრეტული ვადების გარეშე.",
        coords: [41.69444, 43.11855],
    },
    {
      title_ru: "Боржоми — Бакуриани («Кукушка»)",
      title_en: "Borjomi — Bakuriani («Kukushka»)",
      title_ka: "ბორჯომი — ბაკურიანი („კუკუშკა“)",
      description_ru: "Здесь должна быть информация об узкоколейном маршруте Боржоми - Бакуриани («Кукушка»), но он был отменен в 2020. СМИ пишут, что поезду и инфраструктуре требуется ремонт и реконструкция. В мае 2026 года руководство Грузинских железных дорог сообщило о возобновлении маршрута в январе 2027 года.",
      description_en: "Here should be information about the narrow-gauge route Borjomi - Bakuriani («Kukushka»), but it was canceled in 2020. The media write that the train and infrastructure need repair and reconstruction. In May 2026, Georgian Railway management announced the resumption of the route in January 2027.",
      description_ka: "აქ უნდა იყოს ინფორმაცია ბორჯომი - ბაკურიანის ვიწროლიანდაგიანი მარშრუტის შესახებ («კუკუშკა»), მაგრამ ის 2020 წელს გაუქმდა. მედია წერს, რომ მატარებელსა და ინფრასტრუქტურას სჭირდება შეკეთება და რეკონსტრუქცია. 2026 წლის მაისში საქართველოს რკინიგზის ხელმძღვანელობამ განაცხადა მარშრუტის 2027 წლის იანვარში განახლების შესახებ.",
      coords: [41.78172, 43.46672],
    },
    {
      title_ru: "Ветка на Цхинвали",
      title_en: "Tskhinvali line",
      title_ka: "ცხინვალის ხაზი",
      description_ru: "Технически рельсы проложены практически до Цхинвали (и разобраны перед городом), но на практике ветка функционирует только до Гори. Вокзал Цхинвали функционирует как автобусный.",
      description_en: "Technically, the rails are laid almost to Tskhinvali (and dismantled before the city), but in practice the line only operates to Gori. The Tskhinvali station functions as a bus station.",
      description_ka: "ტექნიკურად, რელსები თითქმის ცხინვალამდეა გაყვანილი (და დაშლილია ქალაქის წინ), მაგრამ პრაქტიკაში ხაზის ფუნქციონირება მხოლოდ გორიმდე ხდება. ცხინვალის ვაგზალი ფუნქციონირებს როგორც ავტობუსის სადგური.",
      coords: [42.22909, 43.96977],
    },
    {
      title_ru: "Направление на Карс",
      title_en: "Line towards Kars",
      title_ka: "ყარსის მიმართულება",
      description_ru: "Данная часть железнодорожной сети в направлении Карса используется только для грузовых перевозок.",
      description_en: "This part of the railway network in the direction of Kars is used only for freight traffic.",
      description_ka: "რკინიგზის ეს მონაკვეთი კარის მიმართულებით გამოიყენება მხოლოდ სატვირთო გადაზიდვებისთვის.",
      coords: [41.27316, 43.37754],
    },
]

export class Poi {
  constructor(map, poiData, id) {
    const lang = LanguageService.getCurrentLanguage();
    this.map = map;
    this.title = poiData[`title_${lang}`];
    this.description = poiData[`description_${lang}`];
    this.coords = poiData.coords;
    this.id = id;
    this.createMarker();
    this.show();

    stateManager.subscribe((data) => {
      this.marker.getElement().classList.toggle("active", data.selectedPoi === this);
    });
  }

  createMarker() {
    const markerEl = document.createElement("div");
    markerEl.className = "poi-marker";
    markerEl.setAttribute("data-testid", `poi-${this.id}`);
    markerEl.innerHTML = `<div class="poi-icon">?</div>`;

    // On mobile the description opens in the panel; on desktop the click reaches the map,
    // which toggles the popup
    markerEl.addEventListener("click", (e) => {
      if (stateManager.deviceType !== "mobile") return;
      e.stopPropagation();
      stateManager.selectPoi(this);
      this.map.easeTo({
        center: [this.coords[1], this.coords[0]],
        padding: getBoundsPadding(),
        duration: ANIMATION_DURATION
      });
    });

    this.marker = new maplibregl.Marker({ element: markerEl })
      .setLngLat([this.coords[1], this.coords[0]]);

    this.popup = new maplibregl.Popup({
      offset: 25,
      closeButton: true,
      closeOnClick: true,
      className: "poi-popup",
    }).setHTML(`<div style="max-width: 300px;">${this.description}</div>`);

    this.marker.setPopup(this.popup);
  }

  show() {
    this.marker.addTo(this.map);
  }

  hide() {
    this.marker.remove();
  }
}
