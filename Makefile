run_app:
	python3 app.py & sleep 30

	wget -r http://127.0.0.1:8050/
	wget -r http://127.0.0.1:8050/_dash-layout 
	wget -r http://127.0.0.1:8050/_dash-dependencies

	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-graph.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-highlight.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-markdown.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-datepicker.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-dropdown.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-slider.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/dash_core_components-shared.js
	#wget -r http://127.0.0.1:8050/_dash-component-suites/dash_cytoscape/dash_cytoscape.dev.js

	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dash_table/async-table.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dash_table/async-highlight.js

	wget -r http://127.0.0.1:8050/_dash-component-suites/plotly/package_data/plotly.min.js

	wget -r http://127.0.0.1:8050/assets/style.css

	mv 127.0.0.1:8050 pages_files
	ls -a pages_files
	ls -a pages_files/assets

	find pages_files -exec sed -i.bak 's|_dash-component-suites|BiTComparisonGraphs\\/_dash-component-suites|g' {} \;
	find pages_files -exec sed -i.bak 's|_dash-layout|BiTComparisonGraphs/_dash-layout.json|g' {} \;
	find pages_files -exec sed -i.bak 's|_dash-dependencies|BiTComparisonGraphs/_dash-dependencies.json|g' {} \;
	find pages_files -exec sed -i.bak 's|_reload-hash|BiTComparisonGraphs/_reload-hash|g' {} \;
	find pages_files -exec sed -i.bak 's|_dash-update-component|BiTComparisonGraphs/_dash-update-component|g' {} \;
	find pages_files -exec sed -i.bak 's|assets|BiTComparisonGraphs/assets|g' {} \;

	mv pages_files/_dash-layout pages_files/_dash-layout.json
	mv pages_files/_dash-dependencies pages_files/_dash-dependencies.json
	mv assets/* pages_files/assets/

	ps | grep python | awk '{print $$1}' | xargs kill -9

clean_dirs:
	ls
	rm -rf 127.0.0.1:8050/
	rm -rf pages_files/
	rm -rf joblib