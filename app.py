
from flask import Flask, render_template, request, redirect, url_for, flash
from auto_fill import auto_fill_google_form

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Đổi secret key khi deploy thực tế

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form_url = request.form.get('form_url')
        response_count = request.form.get('response_count')
        if not form_url or not response_count:
            flash('Vui lòng nhập đủ thông tin!')
            return redirect(url_for('index'))
        success, msg = auto_fill_google_form(form_url, response_count)
        if success:
            flash(f'Thành công: {msg}')
        else:
            flash(f'Lỗi: {msg}')
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
